<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv49to50">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv49to50"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>4.9</literal> to <literal>5.0</literal>.
</para>
<xsl:template match="image" mode="conv49to50">
    <xsl:choose>
        <!-- nothing to do if already at 5.0 -->
        <xsl:when test="@schemaversion > 4.9">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="5.0">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv49to50"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv49to50">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv49to50"/>
    </xsl:copy>
</xsl:template>

<!-- convert xen image type to vmx -->
<xsl:template match="type" mode="conv49to50">
    <type>
        <xsl:choose>
            <xsl:when test="@image='xen'">
                <xsl:copy-of select="@*[not(local-name(.) = 'image')]"/>
                <xsl:attribute name="image">
                    <xsl:text>vmx</xsl:text>
                </xsl:attribute>
                <xsl:attribute name="bootkernel">
                    <xsl:text>xenk</xsl:text>
                </xsl:attribute>
                <xsl:attribute name="bootprofile">
                    <xsl:text>xen</xsl:text>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="starts-with(@boot,'xenboot')">
                        <xsl:variable name="bootpath" select="concat('vmxboot',substring(@boot,8))"/>
                        <xsl:attribute name="boot">
                            <xsl:value-of select="$bootpath"/>
                        </xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:copy-of select="@boot"/>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:apply-templates mode="conv49to50"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates mode="conv49to50"/>
            </xsl:otherwise>
        </xsl:choose>
    </type>
</xsl:template>

<!-- add domain="domU" to machine section if parent is in xen mode -->
<xsl:template match="type/machine" mode="conv49to50">
        <machine>
            <xsl:choose>
                <xsl:when test="../@image='xen'">
                    <xsl:attribute name="domain">
                        <xsl:text>domU</xsl:text>
                    </xsl:attribute>
                    <xsl:copy-of select="@*"/>
                    <xsl:apply-templates mode="conv49to50"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy-of select="@*"/>
                    <xsl:apply-templates mode="conv49to50"/>
                </xsl:otherwise>
            </xsl:choose>
        </machine>
</xsl:template>

</xsl:stylesheet>

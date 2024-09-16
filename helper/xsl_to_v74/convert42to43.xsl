<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>


<!-- default rule -->
<xsl:template match="*" mode="conv42to43">
        <xsl:copy>
                <xsl:copy-of select="@*"/>
                     <xsl:apply-templates mode="conv42to43"/>
        </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
        Changed attribute <tag class="attribute">schemaversion</tag>
        to <tag class="attribute">schemaversion</tag> from
        <literal>4.2</literal> to <literal>4.3</literal>. Moved the
        <tag class="attribute">lvmgroup</tag> attribute from the 
        <tag class="element">type</tag> to the 
        <tag class="element">lvmvolumes</tag> element.
</para>
<xsl:template match="image" mode="conv42to43">
    <xsl:choose>
        <!-- nothing to do if already at 4.3 -->
        <xsl:when test="@schemaversion > 4.2">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="4.3">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv42to43"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv42to43">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv42to43"/>
    </xsl:copy>
</xsl:template>

<xsl:template match="preferences" mode="conv42to43">
        <preferences>
                <xsl:copy-of select="@*"/>
                <xsl:apply-templates mode="conv42to43"/>
        </preferences>
</xsl:template>

<xsl:template match="type" mode="conv42to43">
        <xsl:choose>
            <xsl:when test="@lvmgroup">
                    <type>
                        <xsl:copy-of select="@*[local-name() != 'lvmgroup']"/>
                        <xsl:for-each select="*">
                            <xsl:choose>
                                    <xsl:when test="name() = 'lvmvolumes'">
                                            <lvmvolumes>
                                                <xsl:attribute name="lvmgroup">
                                                        <xsl:value-of select="../@lvmgroup"/>
                                                </xsl:attribute>
                                                <xsl:apply-templates mode="conv42to43"/>
                                            </lvmvolumes>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:copy-of select="."/>
                                    </xsl:otherwise>
                            </xsl:choose>
                        </xsl:for-each>
                    </type>
            </xsl:when>
                <xsl:otherwise>
                        <xsl:copy-of select="."/>
                </xsl:otherwise>
        </xsl:choose>
</xsl:template>
</xsl:stylesheet>

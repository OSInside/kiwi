<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv53to54">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv53to54"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>5.3</literal> to <literal>5.4</literal>.
</para>
<xsl:template match="image" mode="conv53to54">
    <xsl:choose>
        <!-- nothing to do if already at 5.4 -->
        <xsl:when test="@schemaversion > 5.3">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="5.4">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv53to54"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- remove type attribute from drivers -->
<para xmlns="http://docbook.org/ns/docbook">
    Remove obsolete type attribute from drivers
</para>
<xsl:template match="drivers" mode="conv53to54">
    <drivers>
        <xsl:copy-of select="@*[not(local-name(.) = 'type')]"/>
        <xsl:apply-templates mode="conv53to54"/>
    </drivers>
</xsl:template>

</xsl:stylesheet>

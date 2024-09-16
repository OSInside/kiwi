<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv59to60">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv59to60"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>5.9</literal> to <literal>6.0</literal>.
</para>
<xsl:template match="image" mode="conv59to60">
    <xsl:choose>
        <!-- nothing to do if already at 6.0 -->
        <xsl:when test="@schemaversion > 5.9">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.0">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv59to60"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv59to60">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv59to60"/>
    </xsl:copy>
</xsl:template>

<!-- remove oem-align-partition -->
<xsl:template match="oemconfig/oem-align-partition" mode="conv59to60">
</xsl:template>

</xsl:stylesheet>
